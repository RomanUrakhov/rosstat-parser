import time


class Profiler(object):

    def __enter__(self):
        self._startTime = time.time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Elapsed time: {:.3f} sec".format(time.time() - self._startTime))
