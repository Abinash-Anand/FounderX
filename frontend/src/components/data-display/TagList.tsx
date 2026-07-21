type Props = {
  items: string[]
  label: string
}

export function TagList({ items, label }: Props) {
  if (items.length === 0) return null
  return (
    <ul className="tag-list" aria-label={label}>
      {items.map((item) => <li key={item}>{item}</li>)}
    </ul>
  )
}
