type Props = {
  title: string
  description: string
}

export function EmptySection({ title, description }: Props) {
  return (
    <div className="empty-section">
      <span aria-hidden="true">—</span>
      <div>
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
  )
}
