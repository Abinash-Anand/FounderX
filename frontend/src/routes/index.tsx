import { createFileRoute } from '@tanstack/react-router'
import { InvestorDashboard } from '../components/InvestorDashboard'

export const Route = createFileRoute('/')({
  component: InvestorDashboard,
})

