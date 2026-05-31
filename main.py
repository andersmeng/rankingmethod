# main.py
import sys
from train import train_walkforward
from monitor import run_monitor
from backtest import run_backtest
from daily_check import run_daily_check

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python main.py [train|monitor|backtest|daily] [--force] [--mail addr]")
        sys.exit(1)
    mode = sys.argv[1].lower()
    force = '--force' in sys.argv or '-f' in sys.argv
    mail_flag = '--mail' in sys.argv
    mail_to = sys.argv[sys.argv.index('--mail') + 1] if mail_flag and len(sys.argv) > sys.argv.index('--mail') + 1 else None
    if mode == 'train':
        train_walkforward(force_download=force)
    elif mode == 'monitor':
        run_monitor(force_download=force)
    elif mode == 'backtest':
        composite = '--composite' in sys.argv
        run_backtest(force_download=force, composite=composite)
    elif mode == 'daily':
        run_daily_check(mail_to=mail_to, force=force)
    else:
        print(f"Unknown mode: {mode}")
