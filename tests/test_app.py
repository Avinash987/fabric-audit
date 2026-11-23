import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from fabric_audit.main import app
from fabric_audit.models import Link

# One client for all tests. It calls the app directly, no server needed.
client = TestClient(app)


# ---------------------------------------------------------------------------
# Test 1: the service is alive
# ---------------------------------------------------------------------------
def test_healthz_returns_200():
    response = client.get("/healthz")
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Test 2: A->B and B->A count as the same cable
#
# Arrange: build the same cable twice, once from each end.
# Act:     get each link's key().
# Assert:  the keys are equal.
# ---------------------------------------------------------------------------
def test_link_direction_does_not_matter():
    # Arrange
    spine_to_leaf = Link(
        interface_a={"device": "spine1", "port": "eth1"},
        interface_b={"device": "leaf1", "port": "eth1"},
    )
    leaf_to_spine = Link(
        interface_a={"device": "leaf1", "port": "eth1"},
        interface_b={"device": "spine1", "port": "eth1"},
    )
    assert spine_to_leaf.key() == leaf_to_spine.key()


# ---------------------------------------------------------------------------
# Test 2b: two DIFFERENT cables must NOT share a key
#
# Why: a key() that returns the same value for everything would pass Test 2.
# This test catches that.
# ---------------------------------------------------------------------------
def test_different_cables_have_different_keys():
    correct_port = Link(
        interface_a={"device": "spine1", "port": "eth1"},
        interface_b={"device": "leaf1", "port": "eth3"},
    )
    wrong_port = Link(
        interface_a={"device": "spine1", "port": "eth1"},
        interface_b={"device": "leaf1", "port": "eth4"},
    )
    assert correct_port.key() != wrong_port.key()


# ---------------------------------------------------------------------------
# Test 3: a cable from a device to itself is rejected
#
# The test PASSES when the code inside the `with` block raises
# ValidationError. If nothing is raised, the test FAILS.
# ---------------------------------------------------------------------------
def test_link_to_same_device_is_rejected():
    with pytest.raises(ValidationError):
        Link(
            interface_a={"device": "leaf1", "port": "eth1"},
            interface_b={"device": "leaf1", "port": "eth2"},
        )
