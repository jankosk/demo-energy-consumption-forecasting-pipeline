import argparse
from pathlib import Path
import pandas as pd


def preprocess(input_path: Path, output_dir: Path):
    df = pd.read_csv(input_path)
    df = process_df(df)

    train_size = 0.1
    test_slice = 24 * 7 * 4
    train_valid_len = int(len(df) * train_size)
    train_len = int(train_valid_len * 0.9)
    test_len = train_valid_len + test_slice

    df_train = df.iloc[:train_len]
    df_valid = df.iloc[train_len:train_valid_len]
    df_test = df.iloc[train_valid_len:test_len]

    if not output_dir.exists():
        output_dir.mkdir()

    df_train.to_csv(output_dir / 'train.csv', index=False)
    df_valid.to_csv(output_dir / 'valid.csv', index=False)
    df_test.to_csv(output_dir / 'test.csv', index=False)


def process_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={'Consumption': 'y', 'Time': 'ds'})
    df = df.convert_dtypes()

    df[['y', 'Temp_outside']] = df[['y', 'Temp_outside']].astype(float)
    df[['Month', 'Day', 'Hour', 'Year']] = df[[
        'Month', 'Day', 'Hour', 'Year']].astype(int)
    df['ds'] = pd.to_datetime(df['ds'])

    df = df.sort_values(by='ds')
    df = df.drop_duplicates(subset=['ds', 'Property_id', 'y'])

    return df


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_path', type=Path)
    parser.add_argument('--output_dir', type=Path, default='./data')
    args = parser.parse_args()

    preprocess(input_path=args.input_path, output_dir=args.output_dir)
