import sys
from popen2 import popen3

class FetchPhotos:
    bin = "gnokii"
    dir = "A:\predefgallery\predefphotos\\"
    dest = "."
    file_list = []

    def __init__(self, **kwargs):
        if "bin" in kwargs:
            self.bin = kwargs["bin"]
        if "dir" in kwargs:
            self.dir = kwargs["dir"]
        if "dest" in kwargs:
            self.dest = kwargs["dest"]

    def fetchList(self):
        (stdout, stdin, stderr) = popen3("%s --getfilelist '%s*.*'" % (self.bin, self.dir))
        list = stdout.readlines()
        # Useless gnokii prompt
        del list[0]
        # Get rid of whitespaces at the ends of the file name
        self.file_list = [x.strip() for x in list]

    def fetchPhoto(self, p):
        print("Fetching file %s..." % p)
        (stdout, stdin, stderr) = popen3("%s --getfile '%s%s' '%s/%s'" % (self.bin,
                self.dir, p, self.dest, p))
        # Make it blocking, so the program will wait for gnokii
        stdout.read(1)

    def fetchAll(self):
        for i in self.file_list:
            self.fetchPhoto(i)

if __name__ == "__main__":
    if len(sys.argv) == 2:
        o = FetchPhotos(dest=sys.argv[1])
    else:
        o = FetchPhotos()
    o.fetchList()
    o.fetchAll()
