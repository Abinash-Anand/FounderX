export const workspaceNavigation = [
  { label: 'Overview', to: '/workspace/overview', marker: 'OV' },
  { label: 'Founder', to: '/workspace/founder', marker: 'FO' },
  { label: 'Career', to: '/workspace/career', marker: 'CA' },
  { label: 'Startups', to: '/workspace/startups', marker: 'ST' },
  { label: 'Projects', to: '/workspace/projects', marker: 'PR' },
  { label: 'Research', to: '/workspace/research', marker: 'RE' },
  { label: 'Evidence', to: '/workspace/evidence', marker: 'EV' },
  { label: 'Founder intelligence', to: '/workspace/intelligence', marker: 'IN' },
  { label: 'Investment memo', to: '/workspace/memo', marker: 'IM' },
] as const

export type WorkspaceRoutePath = (typeof workspaceNavigation)[number]['to']
