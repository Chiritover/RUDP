import random

import tests.BasicTest as BasicTest

"""
This tests random duplicate. We randomly decide to duplicate about half of the
packets that go through the forwarder in either direction.

"""

class SackRandomDuplicateTest(BasicTest.BasicTest):
    def __init__(self, forwarder, input_file):
        super(SackRandomDuplicateTest, self).__init__(forwarder, input_file, sackMode = True)

    def handle_packet(self):
        for p in self.forwarder.in_queue:
            if random.choice([True, False]):
                self.forwarder.out_queue.append(p)
                self.forwarder.out_queue.append(p)
            else:
                self.forwarder.out_queue.append(p)

        # empty out the in_queue
        self.forwarder.in_queue = []