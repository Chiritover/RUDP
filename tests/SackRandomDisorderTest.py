import random

import tests.BasicTest as BasicTest

"""
This tests random disorder. We randomly decide to reorder about half of the
packets that go through the forwarder in either direction.

"""
class SackRandomDisorderTest(BasicTest.BasicTest):
    def __init__(self, forwarder, input_file):
        super(SackRandomDisorderTest, self).__init__(forwarder, input_file, sackMode = True)

    def handle_packet(self):
        for p in self.forwarder.in_queue:
            if random.choice([True, False]):
                self.forwarder.out_queue.append(p)
            else:
                self.forwarder.out_queue.insert(0, p)

        # empty out the in_queue
        self.forwarder.in_queue = []