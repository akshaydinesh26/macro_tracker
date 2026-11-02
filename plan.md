# UI folder structure plan

## Purpose

The `ui/` directory contains the browser-facing frontend. It is separate from
the Python FastAPI backend in `src/macrotracker/`. The frontend should
communicate with the backend over HTTP; it should not import Python modules or
access the backend database directly.

This plan assumes a React + TypeScript frontend built with Vite. Add folders as
the application grows rather than creating empty placeholders up front.

## Current UI scaffold

```text
ui/
├── index.html
├── package.json
├── vite.config.ts
└── src/
    └── main.tsx
```

These files are currently empty, so this is a starting point rather than a
complete frontend architecture.

## Suggested structure

```text
ui/
├── public/
│   └── favicon.svg
├── src/
│   ├── app/
│   │   ├── App.tsx
│   │   └── routes.tsx
│   ├── assets/
│   ├── components/
│   │   ├── layout/
│   │   └── ui/
│   ├── features/
│   │   └── indicators/
│   │       ├── components/
│   │       ├── pages/
│   │       ├── hooks/
│   │       └── types.ts
│   ├── services/
│   │   ├── apiClient.ts
│   │   └── indicators.ts
│   ├── styles/
│   ├── types/
│   └── main.tsx
├── index.html
├── package.json
└── vite.config.ts
```

## Folder and file responsibilities

### `ui/public/`

Contains static files served directly, without being imported or transformed by
the frontend build. Use it for files that need a stable URL, such as a
favicon or `robots.txt`.

For assets imported by TypeScript or CSS and processed by Vite, use
`ui/src/assets/` instead.

### `ui/src/`

Contains frontend application source code. Keep browser-facing code here, and
keep API business logic, persistence, and secrets in the backend.

### `ui/src/main.tsx`

The frontend entry point. It finds the root element in `index.html` and mounts
the React application. Keep setup here minimal; put application components and
feature behavior in their respective modules.

### `ui/src/app/`

Contains application-wide composition, such as the top-level `App` component,
route definitions, and providers that are genuinely shared across the
application. Feature-specific screens and behavior belong under `features/`.

### `ui/src/assets/`

Contains images, icons, and other assets imported by frontend code and
processed by Vite.

### `ui/src/components/`

Contains reusable presentation components used by multiple features.

- `ui/`: general-purpose controls such as buttons, inputs, and cards.
- `layout/`: shared page structure such as navigation, headers, and content
  containers.

Keep indicator-specific components in `features/indicators/` unless they
become useful across multiple features.

### `ui/src/features/`

Groups code by product capability. This keeps a feature's screens, components,
hooks, and types close together.

#### `ui/src/features/indicators/`

The likely home for indicator-related UI, such as an indicator list, detail
view, filters, or display components. Keep feature-only logic here rather than
placing it in a global folder.

- `components/`: components used only by the indicators feature.
- `pages/`: route-level screens for the feature.
- `hooks/`: feature-specific React hooks.
- `types.ts`: types used only within the feature.

### `ui/src/services/`

Contains code that communicates with external systems, especially the FastAPI
backend. Keeping HTTP requests out of UI components makes request handling and
error behavior more consistent.

- `apiClient.ts`: shared HTTP setup, such as the backend base URL and common
  response and error handling.
- `indicators.ts`: indicator-related API functions once the backend provides
  those endpoints.

Do not put API keys or other secrets in frontend code. Anything shipped to a
browser is visible to users.

### `ui/src/styles/`

Contains global styles, design tokens, and styles that are not tied to one
component. Keep component-specific styles with the component when that matches
the project's chosen styling approach.

### `ui/src/types/`

Contains types shared by multiple features, including API response types. Keep
types used by only one feature next to that feature instead.

### `ui/index.html`

The HTML document Vite uses as the frontend entry page. It contains the root
element where the React app mounts and document-level metadata.

### `ui/package.json`

Defines frontend dependencies and scripts, such as development, build, and
test commands. This is separate from the Python dependency configuration in
`pyproject.toml`.

### `ui/vite.config.ts`

Contains Vite development and build configuration. A development proxy can
forward frontend API requests to FastAPI, avoiding hard-coded local backend
URLs in components. Configure the target to match how the backend is run
locally.

## Backend integration

The FastAPI application is in `src/macrotracker/api/`. Its current routes
include `/health`; indicator-specific API routes will be needed before the UI
can load indicator data. The frontend should call those routes through
`ui/src/services/` and represent loading, empty, and error states in the
relevant feature screens.

## Organization guidelines

- Group code by feature first; use shared folders only for genuinely shared
  code.
- Keep UI rendering separate from HTTP requests.
- Keep backend-only logic, configuration, and secrets out of the frontend.
- Avoid creating placeholder folders until there is code to put in them.
- Add tests alongside the feature or component they cover, following the
  frontend test setup once one is selected.
