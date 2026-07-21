import {
  Outlet,
  createRootRoute,
  createRoute,
  createRouter,
  redirect,
} from '@tanstack/react-router'

import { AppLayout } from '../../components/layout/AppLayout'
import { LandingPage } from '../../pages/landing/LandingPage'
import { ResultsPage } from '../../pages/results/ResultsPage'
import { WorkspaceRoute } from '../../pages/workspace/WorkspaceRoute'
import { OverviewPage } from '../../pages/workspace/OverviewPage'
import { FounderPage } from '../../pages/workspace/FounderPage'
import { CareerPage } from '../../pages/workspace/CareerPage'
import { StartupsPage } from '../../pages/workspace/StartupsPage'
import { ProjectsPage } from '../../pages/workspace/ProjectsPage'
import { ResearchPage } from '../../pages/workspace/ResearchPage'
import { EvidencePage } from '../../pages/workspace/EvidencePage'
import { IntelligencePage } from '../../pages/workspace/IntelligencePage'
import { InvestmentMemoPage } from '../../pages/workspace/InvestmentMemoPage'

const rootRoute = createRootRoute({
  component: () => (
    <AppLayout>
      <Outlet />
    </AppLayout>
  ),
  notFoundComponent: () => (
    <main className="page-shell" id="main-content" aria-labelledby="not-found-title">
      <p className="eyebrow">404</p>
      <h1 id="not-found-title">Page not found</h1>
      <a href="/">Return to FounderX</a>
    </main>
  ),
})

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: LandingPage,
})

const resultsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/results',
  component: ResultsPage,
})

const workspaceRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/workspace',
  component: WorkspaceRoute,
})

const workspaceIndexRoute = createRoute({
  getParentRoute: () => workspaceRoute,
  path: '/',
  beforeLoad: () => {
    return redirect({ to: '/workspace/overview' })
  },
})

const workspaceSectionRoutes = [
  createRoute({ getParentRoute: () => workspaceRoute, path: '/overview', component: OverviewPage }),
  createRoute({ getParentRoute: () => workspaceRoute, path: '/founder', component: FounderPage }),
  createRoute({ getParentRoute: () => workspaceRoute, path: '/career', component: CareerPage }),
  createRoute({ getParentRoute: () => workspaceRoute, path: '/startups', component: StartupsPage }),
  createRoute({ getParentRoute: () => workspaceRoute, path: '/projects', component: ProjectsPage }),
  createRoute({ getParentRoute: () => workspaceRoute, path: '/research', component: ResearchPage }),
  createRoute({ getParentRoute: () => workspaceRoute, path: '/evidence', component: EvidencePage }),
  createRoute({ getParentRoute: () => workspaceRoute, path: '/intelligence', component: IntelligencePage }),
  createRoute({ getParentRoute: () => workspaceRoute, path: '/memo', component: InvestmentMemoPage }),
]

const workspaceRouteTree = workspaceRoute.addChildren([workspaceIndexRoute, ...workspaceSectionRoutes])

const routeTree = rootRoute.addChildren([indexRoute, resultsRoute, workspaceRouteTree])

export const router = createRouter({
  routeTree,
  defaultPreload: 'intent',
  defaultPreloadStaleTime: 0,
  scrollRestoration: true,
})

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
