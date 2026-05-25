# ClearPort API Policy

## SECURITY-HOLD

Accounts with `security_hold` set to true must not receive ownership mutations through normal tools.

## ESCALATE-OWNERSHIP

Ownership requests under security hold must be escalated to account review.

## NO-OVERRIDE

Admin override and ownership mutation endpoints are forbidden for this case.
