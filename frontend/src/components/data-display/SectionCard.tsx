import type { PropsWithChildren, ReactNode } from 'react'

type Props = PropsWithChildren<{
  title: string
  description?: string
  action?: ReactNode
  className?: string
}>

export function SectionCard({ title, description, action, className, children }: Props) {
  return (
    <section className={['section-card', className].filter(Boolean).join(' ')}>
      <header className="section-card__header">
        <div>
          <h2>{title}</h2>
          {description ? <p>{description}</p> : null}
        </div>
        {action}
      </header>
      {children}
    </section>
  )
}
