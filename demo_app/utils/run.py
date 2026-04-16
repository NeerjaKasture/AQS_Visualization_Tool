import os
from os.path import join, dirname, abspath
import json
import yaml
import torch
import numpy as np
import xarray as xr
from tqdm import tqdm
from datetime import datetime
from torch.utils.data import DataLoader, Dataset
from box import Box as AttrDict
import argparse
from importlib.machinery import SourceFileLoader
from einops import rearrange

def scale_ds(ds, apply_india_mask):
    with open('data/scale_dict.json') as f:
        scales = json.load(f)
    
    if apply_india_mask:
        mask = np.load('data/india_mask.npz')['arr_0']

    lats = ds['lat'].values
    lons = ds['lon'].values
    lats, lons = np.meshgrid(lats, lons, indexing='ij')
    if apply_india_mask:
        lats = lats[mask]
        lons = lons[mask]

    # scale lat and lon
    lats = (lats - scales['lat']['min']) / (scales['lat']['max'] - scales['lat']['min'])
    lons = (lons - scales['lon']['min']) / (scales['lon']['max'] - scales['lon']['min'])
    
    # scale PM2.5
    var_name = "PM25"
    y = ds[var_name].values
    if apply_india_mask:
        y = y[:, mask]
    y = (np.log(y) - scales[var_name]['mean']) / scales[var_name]['std']
    
    return np.stack([lats, lons], axis=-1), y

class Logger:
    def __init__(self, save_dir, log_file, resume):
        self.save_dir = save_dir
        save_mode = 'a' if resume else 'w'
        self.log_file = open(join(save_dir, log_file), save_mode)

    def log(self, message):
        print(message)
        self.log_file.write(message + '\n')
        self.log_file.flush()

    def close(self):
        self.log_file.close()

class TrainDataset(Dataset):
    def __init__(self, root_path):#, anomalies: bool, crs_7755: bool):        
        self.ds = xr.open_dataset(join(root_path, 'data/train_data.nc'))
        self.x, self.y = scale_ds(self.ds, apply_india_mask=True)

    def __len__(self):
        return len(self.ds['time'])
    
    def __getitem__(self, idx):
        y = self.y[idx]

        c_idx = np.random.choice(len(y), 700, replace=False)
        t_idx = np.random.choice(len(y), 5000, replace=False)
        xc = self.x[c_idx]
        xt = self.x[t_idx]
        yc = y[c_idx]
        yt = y[t_idx]

        return xc, yc, xt, yt
    
class ValDataset(Dataset):
    def __init__(self, root_path, seed):
        self.ds = xr.open_dataset(join(root_path, 'data/val_data.nc'))
        
        self.x, self.y = scale_ds(self.ds, apply_india_mask=False)

        masks = np.load(join(root_path, "data/val_masks.npz"))
        self.c_mask, self.t_mask = masks["c_mask"][seed], masks["t_mask"][seed]
        self.n_per_t = self.c_mask.shape[0]  # samples per time step
        self.t = self.c_mask.shape[1]  # number of time steps
    
    def __len__(self):
        return self.t * self.n_per_t
    
    def __getitem__(self, idx):
        time_idx = idx % self.t
        sample_idx = idx // self.t
        c_mask = self.c_mask[sample_idx, time_idx]
        t_mask = self.t_mask[sample_idx, time_idx]
        xc = self.x[c_mask, :]
        yc = self.y[time_idx, c_mask]
        xt = self.x[t_mask, :]
        yt = self.y[time_idx, t_mask]
        return xc, yc, xt, yt

class TestDataset(Dataset):
    def __init__(self, root_path, c_mask):
        self.ds = xr.open_dataset(join(root_path, 'data/test_data.nc'))
        self.india_mask = np.load(join(root_path, 'data/india_mask.npz'))['arr_0']
        self.x, self.y = scale_ds(self.ds, apply_india_mask=False)

        self.c_mask = c_mask
        self.t = len(self.ds['time'])
    
    def __len__(self):
        return self.t
    
    def __getitem__(self, t):
        xc = self.x[self.c_mask, :]
        yc = self.y[t, self.c_mask]
        xt = self.x[self.india_mask]
        yt = self.y[t, self.india_mask]
        # print(f"{xc.shape=}, {yc.shape=}, {xt.shape=}, {yt.shape=}")
        return xc, yc, xt, yt

class DeployDataset(Dataset):
    def __init__(self, x, y, station_mask):
        self.x = x  # shape (N, 2)
        self.y = y  # shape (T, N)
        self.station_mask = station_mask
        print(f"{self.x.shape=}, {self.y.shape=}, {self.station_mask.shape}")
    
    def __len__(self):
        return self.y.shape[0]  # number of time steps
    
    def __getitem__(self, t):
        xc = self.x[self.station_mask]
        yc = self.y[t, self.station_mask]
        return xc, yc, self.x, self.y[t]

def main():
    # Set random state for reproducibility
    np.random.seed(42)
    torch.manual_seed(42)
    torch.cuda.manual_seed(42)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

    start_time = datetime.now()
    parser = argparse.ArgumentParser()

    # Experiment
    parser.add_argument('--mode', choices=['train', 'validate', 'test', 'deploy'])
    parser.add_argument('--exp_name', type=str)
    parser.add_argument('--resume', action='store_true')
    # parser.add_argument('--resume', action='store_true', help="Resume training from the last checkpoint")

    # Model
    parser.add_argument('--model', type=str)

    # Train
    parser.add_argument('--train_batch_size', type=int)
    parser.add_argument('--lr', type=float)
    parser.add_argument('--num_epochs', type=int)
    parser.add_argument('--eval_freq', type=int)

    # Eval
    parser.add_argument('--eval_batch_size', type=int)

    # Deploy
    parser.add_argument('--num_deployments', type=int, default=10)
    parser.add_argument('--acquisition', choices=['random', 'mean_var', 'max_dist'])

    # Load arguments
    args = parser.parse_args()
    
    # Load the model
    module = SourceFileLoader("nothing", f"models/{args.model}.py").load_module()
    model_cls = getattr(module, args.model.upper())
    with open(f'configs/{args.model}.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Set up the experiment name as time in dd_mm_yyyy_hh_mm_ss format
    log_file = f'{args.mode}_{datetime.now().strftime("%d-%m-%Y_%H:%M:%S:%f")}.txt'
    if args.mode != 'deploy':
        save_dir = f"results/{args.model}/{args.exp_name}"
    else:
        save_dir = f"results/{args.model}/{args.exp_name}/{args.acquisition}"

    os.makedirs(save_dir, exist_ok=True)

    with open(f"{save_dir}/config.yaml", 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    with open(f"{save_dir}/args.json", 'w') as f:
        json.dump(vars(args), f, indent=4)

    # if args.model in ["np", "anp", "cnp", "canp", "bnp", "banp", "tnpd", "tnpa", "tnpnd", "convcnp", "convgnp", "gp", "tabpfn"]:
    model = model_cls(**config)
    # else:
        # raise ValueError(f"Model {args.model} not recognized.")
    
    model.cuda()

    train_loader = DataLoader(
        TrainDataset(root_path='.'),
        batch_size=args.train_batch_size,
        shuffle=True,
        num_workers=4
    )
    with open(join('data', 'scale_dict.json')) as f:
        scales = json.load(f)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    
    first_epoch = 0
    best_val_loss = float('inf')

    if (args.mode in ["validate", "test", "deploy"]) and (args.model not in ["tabpfn", "rf", "idw"]):
        load_dir = save_dir
        if args.mode == "deploy":
            load_dir = f"results/{args.model}/{args.exp_name}"
        model.load_state_dict(torch.load(join(load_dir, 'best.pt')))

    if args.resume:
        ckpt = torch.load(join(save_dir, 'ckpt.pt'), weights_only=False)
        model.load_state_dict(ckpt.model_state_dict)
        optimizer.load_state_dict(ckpt.optimizer_state_dict)
        first_epoch = ckpt.epoch
        best_val_loss = ckpt.best_val_loss
        log_file = ckpt.log_file
        logger = Logger(save_dir, log_file, resume=True)
    else:
        logger = Logger(save_dir, log_file, resume=False)
        logger.log("Config:")
        logger.log(json.dumps(config, indent=4))
        logger.log("Arguments:")
        logger.log(json.dumps(vars(args), indent=4))

    if args.mode == 'train':

        for epoch in range(first_epoch, args.num_epochs):
            model.train()
            loss = 0.0
            init_time = datetime.now()
            for xc, yc, xt, yt in train_loader:
                # print(f"{xc.shape=}, {yc.shape=}, {xt.shape=}, {yt.shape=}")
                batch = AttrDict({
                    'xc': xc.cuda(),
                    'yc': yc.cuda()[..., None],  # Ensure yc is 3D
                    'xt': xt.cuda(),
                    'yt': yt.cuda()[..., None]  # Ensure yt is 3D
                })
                batch.x = torch.cat([batch.xc, batch.xt], dim=1)
                batch.y = torch.cat([batch.yc, batch.yt], dim=1)

                optimizer.zero_grad()
                outs = model(batch)
                loss = outs.loss
                loss.backward()
                optimizer.step()
                loss += outs.loss.item()
            epoch_time = datetime.now() - init_time
            loss /= len(train_loader)
            vram = torch.cuda.max_memory_allocated() / (1024 ** 3)  # Convert to GB
            logger.log(f"Epoch {epoch+1}/{args.num_epochs}, Loss: {loss:.6f}, VRAM: {vram:.2f} GB, Time: {epoch_time}")

            if (epoch + 1) % args.eval_freq == 0:
                logger.log(f"Validating at epoch {epoch + 1}...")
                avg_val_loss, avg_rmse = validate(model, args, scales, logger)

                if avg_val_loss < best_val_loss:
                    best_val_loss = avg_val_loss
                    torch.save(model.state_dict(), join(save_dir, 'best.pt'))
                    logger.log(f"Best model saved with validation loss: {best_val_loss:.6f}")
            
            # save checkpoint
            box = AttrDict({
                'epoch': epoch + 1,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'best_val_loss': best_val_loss,
                'log_file': log_file
            })
            torch.save(box, join(save_dir, f'ckpt.pt'))
    
        logger.log(f"Training completed in {datetime.now() - start_time}")
    
    elif args.mode == 'validate':
        logger.log("Validating...")
        avg_val_loss, avg_rmse = validate(model, args, scales, logger)
    elif args.mode == 'test':
        logger.log("Testing...")
        c_mask = np.load("data/station_mask.npz")['arr_0']
        loss, rmse = test_it(model, args, scales, logger, c_mask)
    elif args.mode == "deploy":
        logger.log("Deploying Sensors")
        deploy(model, args, scales, logger, save_dir)
    else:
        raise ValueError(f"Mode {args.mode} not recognized.")
    
def deploy(model, args, scales, logger, save_dir):
    model.eval()

    # station mask
    india_mask = np.load("data/india_mask.npz")['arr_0']
    sensors_mask = np.load("data/station_mask.npz")['arr_0']
    mask = sensors_mask[india_mask]

    # Initial testing
    # Test it
    c_mask = sensors_mask.copy()
    c_mask[india_mask] = mask
    logger.log(f"Testing with {c_mask.sum()} deployed sensors")
    loss, rmse = test_it(model, args, scales, logger, c_mask)

    # load validation data
    ds = xr.open_dataset('data/val_data.nc')
    x, y = scale_ds(ds, apply_india_mask=True)

    for i in tqdm(range(args.num_deployments)):
        t = len(ds['time'])
        n = len(mask)
        pred_var = np.zeros((t, n)) * np.nan

        if args.acquisition == "random":
            scores = np.random.rand(pred_var.shape[1])
            scores[mask] = -np.inf  # Set scores of already deployed sensors to -inf
        elif args.acquisition == "max_dist":
            scores = np.zeros(pred_var.shape[1])
            dxc = x[mask] # (M, 2)
            dxt = x  # (N, 2)
            print(f"{dxc.shape=}, {dxt.shape=}")
            scores = np.linalg.norm(dxc[:, None, :] - dxt[None, :, :], axis=-1).mean(axis=0) # (N,)
            scores[mask] = -np.inf
        else:
            # Dataloader
            loader = DataLoader(
                DeployDataset(x, y, mask),
                batch_size=args.eval_batch_size,
                shuffle=False,
                num_workers=4
            )

            # Get predictive variance
            with torch.no_grad():
                batch_idx = 0
                for xc, yc, xt, yt in tqdm(loader):
                    # print(f"{xc.shape=}, {yc.shape=}, {xt.shape=}, {yt.shape=}")
                    xc, yc, xt, yt = xc.cuda(), yc.cuda()[..., None], xt.cuda(), yt.cuda()[..., None]
                    batch_size = 3000
                    n_batches = yt.shape[1] // batch_size + 1
                    for i in tqdm(range(n_batches)):
                        # print(f"{torch.cuda.memory_allocated() / (1024 ** 3):.2f} GB")
                        xt_ = xt[:, i*batch_size:(i+1)*batch_size, :]
                        yt_ = yt[:, i*batch_size:(i+1)*batch_size]
                        # print(f"{xc.shape=}, {yc.shape=}, {xt_.shape=}")
                        # print(f"Number of NaNs in xc: {torch.isnan(xc).sum().item()}")
                        # print(f"Number of NaNs in yc: {torch.isnan(yc).sum().item()}")
                        # print(f"Number of NaNs in xt_: {torch.isnan(xt_).sum().item()}")
                        # print(f"Number of NaNs in yt_: {torch.isnan(yt_).sum().item()}")
                        dist = model.predict(xc, yc, xt_)
                        # print(f"{xt_.shape=}, {yt_.shape=}, {dist.loc.shape=}, {dist.variance.shape=} {batch_idx=} {batch_size=} {pred_var.shape=}")
                        pred_var[batch_idx:batch_idx + xt_.shape[0], i*batch_size:(i+1)*batch_size] = dist.variance.cpu().numpy().squeeze()
                        # loss -= dist.log_prob(yt_).sum().item()
                        # yt_ = np.exp(yt_.cpu().numpy() * scales['PM25']['std'] + scales['PM25']['mean'])
                        # yt_pred = np.exp(dist.loc.cpu().numpy() * scales['PM25']['std'] + scales['PM25']['mean'])
                        # mse += np.sum((yt_ - yt_pred) ** 2)
                        # n += yt_.ravel().shape[0]
                    batch_idx += xt.shape[0]
            assert np.isnan(pred_var).sum() == 0, "NaN values found in predictive variance"
            
            if args.acquisition == "mean_var":
                scores = pred_var.mean(axis=0)  # Average over time

        # remove already deployed sensors
        scores[mask] = -np.inf  # Set scores of already deployed sensors to -inf

        # Deploy a sensor
        deploy_idx = np.argmax(scores)
        logger.log(f"Deployment {i+1}: Deploying sensor at index {deploy_idx} with score {scores[deploy_idx]:.6f}")

        # Update the mask to include the newly deployed sensor
        mask[deploy_idx] = True

        # Test it
        c_mask = np.zeros_like(india_mask, dtype=bool)
        c_mask[india_mask] = mask
        logger.log(f"Testing with {c_mask.sum()} deployed sensors")
        loss, rmse = test_it(model, args, scales, logger, c_mask)

        # # Save the final mask of deployed sensors
        # os.makedirs(join(save_dir, args.acquisition), exist_ok=True)
        # np.savez(join(save_dir, args.acquisition, 'tmp_deployed_sensors.npz'), arr_0=mask, )
        # Save the final mask of deployed sensors
        os.makedirs(save_dir, exist_ok=True)
        np.savez(join(save_dir, 'tmp_deployed_sensors.npz'), arr_0=mask)
    np.savez(join(save_dir, 'deployed_sensors.npz'), arr_0=mask)

def validate(model, args, scales, logger):
    model.eval()
    val_losses = []
    val_rmse = []

    for seed in range(5):
        val_loader = DataLoader(
            ValDataset(root_path='.', seed=seed),
            batch_size=args.eval_batch_size,
            shuffle=False,
            num_workers=4
        )
        val_loss = 0.0
        mse = 0.0
        n = 0
        with torch.no_grad():
            for xc, yc, xt, yt in val_loader:
                xc, yc, xt, yt = xc.cuda(), yc.cuda()[..., None], xt.cuda(), yt.cuda()[..., None]
                dist = model.predict(xc, yc, xt)
                val_loss -= dist.log_prob(yt).sum().item()
                yt_ = np.exp(yt.cpu().numpy() * scales['PM25']['std'] + scales['PM25']['mean'])
                yt_pred = np.exp(dist.loc.cpu().numpy() * scales['PM25']['std'] + scales['PM25']['mean'])
                mse += np.sum((yt_ - yt_pred) ** 2)
                n += yt_.ravel().shape[0]
        mse /= n
        val_loss /= n
        val_losses.append(val_loss)
        val_rmse.append(mse ** 0.5)
        logger.log(f"Validation Loss (seed {seed}): {val_loss:.6f}, RMSE: {np.sqrt(mse):.6f}")
    avg_val_loss = np.mean(val_losses)
    std_val_loss = np.std(val_losses)
    avg_rmse = np.mean(val_rmse)
    std_rmse = np.std(val_rmse)
    logger.log(f"Average Validation Loss: {avg_val_loss:.6f} with std {std_val_loss:.6f}, RMSE: {avg_rmse:.6f} with std {std_rmse:.6f}")
    return avg_val_loss, avg_rmse

def test_it(model, args, scales, logger, c_mask):
    time_init = datetime.now()
    model.eval()

    loader = DataLoader(
        TestDataset(root_path='.', c_mask=c_mask),
        batch_size=args.eval_batch_size,
        shuffle=False,
        num_workers=4
    )
    loss = 0.0
    mse = 0.0
    n = 0
    from tqdm import tqdm
    with torch.no_grad():
        for xc, yc, xt, yt in tqdm(loader):
            # print(f"{xc.shape=}, {yc.shape=}, {xt.shape=}, {yt.shape=}")
            xc, yc, xt, yt = xc.cuda(), yc.cuda()[..., None], xt.cuda(), yt.cuda()[..., None]
            batch_size = 3000
            n_batches = yt.shape[1] // batch_size + 1
            for i in tqdm(range(n_batches)):
                # print(f"{torch.cuda.memory_allocated() / (1024 ** 3):.2f} GB")
                xt_ = xt[:, i*batch_size:(i+1)*batch_size, :]
                yt_ = yt[:, i*batch_size:(i+1)*batch_size]
                # print(f"{xc.shape=}, {yc.shape=}, {xt_.shape=}")
                # print(f"Number of NaNs in xc: {torch.isnan(xc).sum().item()}")
                # print(f"Number of NaNs in yc: {torch.isnan(yc).sum().item()}")
                # print(f"Number of NaNs in xt_: {torch.isnan(xt_).sum().item()}")
                # print(f"Number of NaNs in yt_: {torch.isnan(yt_).sum().item()}")
                dist = model.predict(xc, yc, xt_)
                loss -= dist.log_prob(yt_).sum().item()
                yt_ = np.exp(yt_.cpu().numpy() * scales['PM25']['std'] + scales['PM25']['mean'])
                yt_pred = np.exp(dist.loc.cpu().numpy() * scales['PM25']['std'] + scales['PM25']['mean'])
                mse += np.sum((yt_ - yt_pred) ** 2)
                n += yt_.ravel().shape[0]
    mse /= n
    loss /= n
    rmse = mse ** 0.5
    logger.log(f"Test Loss: {loss:.6f}, RMSE: {rmse:.6f}")
    logger.log(f"Max VRAM usage: {torch.cuda.max_memory_allocated() / (1024 ** 3):.2f} GB")
    logger.log(f"Testing completed in {datetime.now() - time_init}")
    return loss, rmse

if __name__ == "__main__":
    main()