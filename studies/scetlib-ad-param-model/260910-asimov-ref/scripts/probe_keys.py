import sys, h5py

with h5py.File(sys.argv[1], "r") as f:

    def w(n, o):
        if isinstance(o, h5py.Dataset):
            print(f"{n:60s} {str(o.shape):20s} {o.dtype}")

    f.visititems(w)
