# Restaurant Platform Plan

## Goal

Build and maintain a complete restaurant platform around the existing
SQLAlchemy models. The implemented platform includes menu CRUD, QR ordering,
staff authentication, kitchen workflows, and billing without changing the
historical migration contract unnecessarily.

## Current status

The menu, table, order, billing, authentication, and frontend workspaces are
implemented. Remaining work is focused on automated coverage, operational
hardening, and deployment documentation.

## Current Model Contract

- `Item`: `id`, `name`, `base_price_paisa`, related option groups, and item-specific options.
- `OptionGroup`: `id`, `name`, related items, and child options.
- `Option`: `id`, `name`, `group_id`.
- `ItemOption`: composite key of `item_id` and `option_id`, with `extra_price_paisa`.
- `item_option_groups`: many-to-many relationship between items and option groups.
- Foreign keys use cascade deletion. Existing migrations must be treated as the database contract.

## Completed foundation

- Confirm the async database session dependency is exposed for FastAPI routes.
- Confirm all menu models are imported into Alembic metadata, including `ItemOption` and the association table.
- Package imports use the `src` layout.
- `DATABASE_URL` is loaded from `.env` before application or migration imports.
- Existing migrations remain unchanged; new schema changes use reviewed migrations.

## Implemented API contract

Pydantic v2 schemas in `src/restaurant_api/schemas/` separate input, update,
and output models. Response models use `ConfigDict(from_attributes=True)`.

### Shared validation

- Trim names and reject empty values.
- Enforce the model limits: item names up to 150 characters and group/option names up to 100 characters.
- Require non-negative integer prices in paisa.
- Keep prices as integer paisa values in the API; do not use floating-point currency values.
- Use `PositiveInt` or equivalent validation for resource IDs where appropriate.

### Item schemas

- `ItemCreate`: `name`, `base_price_paisa`, optional option-group IDs, and optional item-option prices.
- `ItemUpdate`: all editable fields optional, with clear handling for omitted versus explicitly empty relationships.
- `ItemOptionPriceCreate` or equivalent: `option_id`, `extra_price_paisa`.
- `ItemOptionPriceUpdate`: optional `extra_price_paisa`.
- `ItemRead`: `id`, `name`, `base_price_paisa`, and nested option-group/option data suitable for menu display.

### Option group schemas

- `OptionGroupCreate`: `name`, optionally including initial options.
- `OptionGroupUpdate`: optional `name` and a deliberate policy for replacing or editing child options.
- `OptionGroupRead`: `id`, `name`, and nested options.

### Option schemas

- `OptionCreate`: `name`, `group_id` or creation through a group endpoint.
- `OptionUpdate`: optional `name` and, only if supported, a controlled group reassignment.
- `OptionRead`: `id`, `name`, and `group_id`.

### Response shape decision

Use shallow schemas for write requests and nested schemas for read responses. Avoid returning unrestricted recursive relationships such as item -> group -> items. Keep `ItemOption` association pricing visible in item responses so clients can distinguish a base option from an item-specific extra charge.

## Implemented routes

Routers are registered from `main.py` under `/api/auth`, `/api/menu`,
`/api/tables`, and the customer/admin order paths.

### Item endpoints

- `POST /api/menu/items` creates an item and its optional group/option associations.
- `GET /api/menu/items` lists items with predictable ordering, required menu relationships loaded, and `page`/`page_size` pagination.
- `GET /api/menu/items/{item_id}` returns one complete menu item or `404`.
- `PATCH /api/menu/items/{item_id}` updates scalar fields and explicitly requested relationships.
- `DELETE /api/menu/items/{item_id}` deletes the item and its dependent associations, returning `204`.

### Option group endpoints

- `POST /api/menu/option-groups` creates a group.
- `GET /api/menu/option-groups` lists groups with their options and `page`/`page_size` pagination.
- `GET /api/menu/option-groups/{group_id}` returns one group or `404`.
- `PATCH /api/menu/option-groups/{group_id}` updates the group name.
- `DELETE /api/menu/option-groups/{group_id}` deletes the group according to the existing cascade behavior.

### Option endpoints

- `POST /api/menu/options` creates an option under an existing group.
- `GET /api/menu/options` lists options with `page`/`page_size` pagination and an optional `group_id` filter.
- `GET /api/menu/options/{option_id}` returns one option or `404`.
- `PATCH /api/menu/options/{option_id}` updates allowed fields.
- `DELETE /api/menu/options/{option_id}` deletes the option and its item-option associations.

### Item-option association endpoints

Choose one consistent public API. Prefer item-scoped operations because extra pricing belongs to an item:

- `PUT /api/menu/items/{item_id}/options/{option_id}` creates or replaces the item-specific extra price.
- `DELETE /api/menu/items/{item_id}/options/{option_id}` removes that item-specific price.

If an item assigns option groups, validate that assigned options belong to one of those groups before creating the association. Return `400` for an invalid relationship and `404` when either resource does not exist.

## Transaction and query rules

- Use `AsyncSession` for every route and commit once per successful command.
- Call `flush()` when IDs are needed before creating related records, then refresh the final response.
- Roll back on command failure before returning an error.
- Use explicit eager-loading options such as `selectinload` for response relationships; do not rely on lazy loading after an async session operation.
- Use `result.scalars()` or `result.unique().scalars()` appropriately when loading joined relationships.
- Translate missing resources to `404`, invalid relationship references to `400` or `422` according to the API contract, and duplicate composite associations to a clear client error.
- Keep deletion behavior consistent with the database foreign-key cascades and ORM relationship cascades.

## Remaining validation and delivery work

Add or expand focused tests for:

- Schema validation for blank names, maximum lengths, negative prices, and omitted versus empty update fields.
- Item CRUD, including base price and nested reads.
- Option group and option CRUD.
- Item-option extra price create, update, and delete.
- `404` responses for missing resources.
- Invalid group/option/item relationships.
- Delete behavior and cascade cleanup.
- Async relationship loading in list and detail responses.
- Login, token expiry, inactive users, and admin/kitchen authorization.
- Customer orderer-token claiming and concurrent claims.
- Bill totals, cancelled orders, payment confirmation, and session closure.
- Frontend auth redirects, kitchen routes, and customer ordering.

Run the following checks during implementation:

```bash
uv run python -m compileall src
uv run alembic check
uv run pytest
uv run uvicorn restaurant_api.main:app --reload
```

Verify the OpenAPI document at `/docs` and manually exercise the happy path: create an option group, add options, create an item, attach the group and item-specific prices, read the complete menu item, update it, and delete it.

## Definition of done

- All four menu concepts have documented, validated API behavior.
- Request schemas are separate from response schemas and do not expose recursive ORM graphs.
- Async database operations commit, roll back, and eagerly load relationships correctly.
- Existing migrations remain unchanged unless a new reviewed migration is required.
- CRUD and relationship edge cases have automated coverage.
- The API is registered and visible in OpenAPI documentation.
- Staff authentication and role restrictions are documented and tested.
- Frontend lint and production build pass.
