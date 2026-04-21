from app.policies.collector_policy import collector_policy
from app.policies.dealer_policy import dealer_policy
from app.policies.healer_policy import healer_policy
from app.policies.scout_policy import scout_policy
from app.policies.support_policy import support_policy
from app.policies.tank_policy import tank_policy

ROLE_POLICIES = [
    healer_policy,
    tank_policy,
    collector_policy,
    dealer_policy,
    support_policy,
    scout_policy,
]
