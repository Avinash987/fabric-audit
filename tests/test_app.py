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
        interface_a={"device_name": "spine1", "name": "eth1"},
        interface_b={"device_name": "leaf1", "name": "eth1"},
    )
    leaf_to_spine = Link(
        interface_a={"device_name": "leaf1", "name": "eth1"},
        interface_b={"device_name": "spine1", "name": "eth1"},
    )
    assert spine_to_leaf.key() == leaf_to_spine.key()


# ---------------------------------------------------------------------------
# Test 3: a cable from a device to itself is rejected
#
# The test PASSES when the code inside the `with` block raises
# ValidationError. If nothing is raised, the test FAILS.
# ---------------------------------------------------------------------------
def test_link_to_same_device_is_rejected():
    with pytest.raises(ValidationError):
        Link(
            interface_a={"device_name": "leaf1", "name": "eth1"},
            interface_b={"device_name": "leaf1", "name": "eth2"},
        )
