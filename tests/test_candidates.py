from time import time

from ..tool.tracker import TrackerCommunity
from .debugcommunity.community import DebugCommunity
from .dispersytestclass import DispersyTestClass, call_on_dispersy_thread


class TestCandidates(DispersyTestClass):

    @call_on_dispersy_thread
    def test_get_introduce_candidate(self):
        self.__test_introduce(DebugCommunity.create_community)

    @call_on_dispersy_thread
    def test_tracker_get_introduce_candidate(self):
        communities, candidates = self.__test_introduce(TrackerCommunity.create_community)

        # trackers should not prefer either stumbled or walked candidates, i.e. it should not return
        # candidate 1 more than once/in the wrong position
        now = time()
        c = communities[0]

        candidates[0].walk(c, now, 10.5)
        candidates[0].walk_response(c)

        expected = [("127.0.0.1", 5), ("127.0.0.1", 1), ("127.0.0.1", 2), ("127.0.0.1", 3), ("127.0.0.1", 4)]
        got = []

        for candidate in candidates:
            candidate.stumble(c, now)

            candidate = c.dispersy_get_introduce_candidate(candidate)
            got.append(candidate.lan_address if candidate else None)

        self.assertEquals(expected, got)

    @call_on_dispersy_thread
    def __test_introduce(self, community_create_method):
        c = community_create_method(self._dispersy, self._my_member)
        candidates = []
        for i in range(5):
            address = ("127.0.0.1", i + 1)
            candidate = c.create_candidate(address, False, address, address, u"unknown")
            candidates.append(candidate)

        now = time()
        expected = [None, ("127.0.0.1", 1), ("127.0.0.1", 2), ("127.0.0.1", 3), ("127.0.0.1", 4)]
        got = []

        for candidate in candidates:
            candidate.stumble(c, now)

            candidate = c.dispersy_get_introduce_candidate(candidate)
            got.append(candidate.lan_address if candidate else None)

        self.assertEquals(expected, got)

        # ordering should not interfere between communities
        expected = [None, ("127.0.0.1", 5), ("127.0.0.1", 4), ("127.0.0.1", 3), ("127.0.0.1", 2)]
        got = []

        c2 = community_create_method(self._dispersy, self._my_member)
        for candidate in reversed(candidates):
            candidate.stumble(c2, now)

            candidate = c2.dispersy_get_introduce_candidate(candidate)
            got.append(candidate.lan_address if candidate else None)

        self.assertEquals(expected, got)
        return [c, c2], candidates

    @call_on_dispersy_thread
    def test_merge_candidates(self):
        c = DebugCommunity.create_community(self._dispersy, self._my_member)

        # let's make a list of all possible combinations which should be merged into one candidate
        candidates = []
        candidates.append(c.create_candidate(("1.1.1.1", 1), False, ("192.168.0.1", 1), ("1.1.1.1", 1), u"unknown"))
        candidates.append(c.create_candidate(("1.1.1.1", 2), False, ("192.168.0.1", 1), ("1.1.1.1", 2), u"symmetric-NAT"))
        candidates.append(c.create_candidate(("1.1.1.1", 3), False, ("192.168.0.1", 1), ("1.1.1.1", 3), u"symmetric-NAT"))
        candidates.append(c.create_candidate(("1.1.1.1", 4), False, ("192.168.0.1", 1), ("1.1.1.1", 4), u"unknown"))

        self._dispersy._filter_duplicate_candidate(candidates[0])

        expected = [candidates[0].wan_address]

        got = []
        for candidate in c._candidates.itervalues():
            got.append(candidate.wan_address)

        self.assertEquals(expected, got)
