from qianji_converter import convert_bea_to_qianji


if __name__ == '__main__':
    input_csv = '/Users/huzhe/playground/hsbc2qianji/data/BEA_Full_Statement_2026-01-17.csv'
    output_csv = '/Users/huzhe/playground/hsbc2qianji/data/BEA_Qianji_Output.csv'

    print(f'Converting {input_csv} to {output_csv}...')
    convert_bea_to_qianji(input_csv, output_csv)
    print('Conversion complete.')