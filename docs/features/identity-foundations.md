# Identity Foundations

## Purpose

Establish the identity and account foundation for the Wingspan Stats Portal.

The feature will allow invited users to register for an account, require administrator approval before access is granted, and establish a one-to-one relationship between a Django user account and a Wingspan Player.

This feature provides the identity foundation required by future features such as Personal Dashboards and Game Management.

---

## Core Identity Model

Django `User` and Wingspan `Player` will remain separate concepts.

### User

A User represents the person's application account and authentication identity.

A user will have:

* Name
* Username
* Email address
* Password
* Django account and permission attributes

Usernames must be unique.

### Player

A Player represents the person's identity within Wingspan game data.

A Player will have:

* Unique Player name
* Active status
* Optional relationship to a Django User

Player names must remain unique so Players can be clearly distinguished throughout the application.

### User-to-Player Relationship

The following rules apply:

* A User may be linked to at most one Player.
* A Player may be linked to at most one User.
* A Player may exist without a User.
* Existing Player records and historical game data must remain valid.
* The relationship should be enforced by the database where practical.

---

## Registration

Registration will be invite-only.

A shared registration invite code will be configured outside source control, such as through an environment variable.

Possession of the invite code permits someone to submit a registration request. It does **not** grant access to the application.

All new accounts require administrator approval before they become active.

### Registration Information

Registration will collect:

* Name
* Username
* Email address
* Password
* Invite code
* Player selection or new Player name

### Existing Player

A registrant may request to link their account to an existing Player that does not already have a User.

The relationship does not become approved solely because the registrant selected that Player.

The administrator must approve the account and Player relationship.

A Player already linked to another User cannot be claimed.

### New Player

A registrant who does not already exist as a Player may request creation of a new Player.

The requested Player name must be unique.

If that Player name already exists, the registrant should be directed toward the existing-Player registration path rather than creating a duplicate Player.

---

## Authentication

The application will continue using Django's authentication system.

The application will provide:

* Login
* Logout
* Authentication-aware navigation
* A basic account/profile view

Once authenticated, the application must be able to reliably determine the Player associated with the current User.

Existing Django staff, superuser, and Admin functionality must continue to work.

---

## Account Approval

Newly registered accounts will not receive authenticated application access until approved by an administrator.

Administrator approval should verify:

* The registration is legitimate.
* The requested Player relationship is appropriate.
* The Player is not already associated with another User.

Once approved, the account becomes active and the User-to-Player relationship becomes authoritative.

---

## Account Recovery

Password management will continue using Django's authentication system.

For the initial implementation, password recovery may be handled administratively through Django Admin.

Email-based password reset may be added later without requiring a redesign of the identity model.

---

## Out of Scope

Identity Foundations will not implement:

* Personal Dashboard
* Achievements
* User game submission
* Game confirmation
* Game disputes
* Game revision history
* Game-level authorization
* External IAM or identity providers

These features may build upon Identity Foundations later.

---

# Implementation Phases

## Phase 1 — Identity Model

* Establish the User-to-Player relationship.
* Add required database constraints.
* Create and apply migrations.
* Link existing users to their existing Player records.
* Verify existing Player, Game, and GameResult data remains intact.

## Phase 2 — Authentication UI

* Implement application login.
* Implement logout.
* Update navigation based on authentication state.
* Add a basic authenticated account/profile view.
* Verify existing staff and Admin functionality.

## Phase 3 — Invite-Only Registration

* Add invite-code validation.
* Add account registration.
* Support requesting an existing unlinked Player.
* Support requesting creation of a new Player with a unique name.
* Create new accounts in a state requiring administrator approval.
* Prevent conflicting or duplicate Player relationships.

## Phase 4 — Account Approval

* Establish the administrator approval workflow.
* Allow administrators to review the requested Player relationship.
* Activate approved accounts.
* Ensure rejected or unapproved accounts cannot authenticate.

## Phase 5 — Account Recovery

* Establish the initial administrator-assisted password-reset procedure.
* Leave email-based password recovery for a future enhancement.

## Phase 6 — Integration and Testing

Verify:

* Invite-code enforcement
* Registration
* Administrator approval
* Login and logout
* Existing Player claiming
* New Player creation
* Unique Player names
* User-to-Player constraints
* Existing account migration
* Staff and Admin access
* Historical game data integrity
* Reliable access to the authenticated User's Player
