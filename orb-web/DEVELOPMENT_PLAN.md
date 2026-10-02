# ORB Frontend Development Plan

## Current architecture

- React 19 and Vite 7; `index.html` mounts the app from `src/main.jsx`.
- The app is a single `App` component. It handles page and role selection with `useState`. Page components and sample product and order data also live in `main.jsx`; there is no routing library or separate data/service layer.
- `src/styles.css` contains the theme, page styles, and responsive breakpoints. Icons use `lucide-react`; fonts and product and hero images load from external URLs.
- There is no backend connection. Products and orders are fixed demo data, and cart contents are held in memory and reset on reload.

## Existing functionality

- Public landing page with customer and farmer entry points.
- Customer and farmer sign-in and sign-up screens, followed by role-specific demo navigation.
- Customer home, product search and category filtering, cart quantity and removal controls, checkout confirmation, order list and details, and account views.
- Farmer dashboard, verification status display, product list, add/edit form view, and profile.
- Responsive desktop, tablet, and mobile layouts.

These flows are prototype interactions. Authentication, form submission, checkout/payment, order status, filtering/sorting, product editing, notifications, location selection, image upload, and ratings are not backed by persistent data. Some visible controls are placeholders or have no action.

## Recommended component structure

Keep the existing visual design while splitting `main.jsx` into focused modules:

```text
src/
  app/              App, route definitions, providers
  components/       shared header, footer, buttons, fields, cards, status
  features/
    auth/           login, registration, session views
    catalog/        product list, filters, product cards
    cart/           cart and order summary
    checkout/       address and payment steps
    orders/         order list, detail, status timeline
    farmer/         dashboard, inventory, verification, profile
    account/        customer account
  services/         API client and feature API modules
  data/             temporary fixtures, removed as endpoints become available
  styles/           theme and feature styles
```

Adopt React Router when real URLs and navigation history are introduced. Keep the shared header and footer in the application layout, and add role-aware route protection when authentication exists.

## Recommended API structure

Use one configurable API base URL and a shared fetch client for JSON, credentials/token handling, and consistent error parsing. Group endpoint calls by feature:

- `auth`: register, login, logout, current session, password reset.
- `products`: list/search/filter, product details, farmer create/update/archive, image upload.
- `farmers`: profile, verification application, verification status.
- `cart` and `addresses`: retrieve/update cart, saved delivery addresses, delivery availability/quote.
- `orders`: create order, list customer/farmer orders, order details, status updates.
- `payments`: create/confirm payment and receive payment status from the server.
- `reviews`: submit and list product ratings/reviews.

The backend should calculate prices, stock, delivery charges, and order totals. The frontend should display server results and handle loading, empty, and error states.

## Recommended state management

- Use TanStack Query for server data, caching, refetching, and mutations once APIs exist.
- Keep temporary UI state, such as open menus and selected filters, local to the relevant component.
- Use a small shared context or Zustand store for client-only cart state until cart persistence moves to the API. Avoid duplicating server-owned cart data.
- Keep authentication/session data in one auth provider, and have route guards read from it.
- Use a form library such as React Hook Form with schema validation for authentication, product, and address forms.

## Recommended frontend phases

1. **Foundation:** Split the monolithic entry point into the proposed feature/component structure, introduce routes, and preserve the current design and demo flows.
2. **Authentication and farmer onboarding:** Connect session flows and farmer verification; add protected role-specific pages and form validation.
3. **Catalog and inventory:** Connect product listing/search/filtering and farmer inventory CRUD/image upload, including loading and error states.
4. **Cart, addresses, and checkout:** Persist cart/address state, request server totals, and integrate payment confirmation.
5. **Orders and feedback:** Connect order history/details/status, notifications, and product reviews.
6. **Quality and release:** Add accessibility and responsive checks, automated coverage for core flows, and production configuration/monitoring.

## Verification performed

- `npm install`: completed; 0 vulnerabilities reported.
- `npm run dev -- --host 127.0.0.1`: Vite started at `http://127.0.0.1:5174/` because port 5173 was occupied; HTTP check returned 200.
- `npm run build`: completed successfully with no warnings or errors.
