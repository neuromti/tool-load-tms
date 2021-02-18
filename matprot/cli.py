def main():
    import argparse
    import numpy as np
    from matprot.convert.traces import convert_mat

    parser = argparse.ArgumentParser(
        prog="matprot",
        description="convert TMS data from the legacy protocols, i.e. from .mat into .npy",
    )
    parser.add_argument(
        "-f",
        "--from",
        nargs="+",
        help="Which .mat file to use",
        required=True,
        dest="matfile",
    )
    parser.add_argument(
        "-t",
        "--to",
        nargs="+",
        help="Which .npy file to convert into",
        required=True,
        dest="npyfile",
    )

    # parse and run respective subcommands
    args, _ = parser.parse_known_args()
    print(args)
    content = convert_mat(args.matfile)
    np.save(args.npyfile, content)


if __name__ == "__main__":
    main()

