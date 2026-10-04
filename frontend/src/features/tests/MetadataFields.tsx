import { useState } from 'react'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { Field } from '../../components/Feedback'

function textValue(value: unknown): string { return typeof value === 'string' ? value : JSON.stringify(value) }

export function MetadataFields({ title, values, onChange, hiddenKeys = [] }: { title: string; values: Record<string, unknown>; onChange: (values: Record<string, unknown>) => void; hiddenKeys?: readonly string[] }) {
  const [key, setKey] = useState(''), [value, setValue] = useState('')
  const visible = Object.entries(values).filter(([name]) => !hiddenKeys.includes(name))
  function update(name: string, nextValue: string) { onChange({ ...values, [name]: typeof values[name] === 'number' && nextValue !== '' ? Number(nextValue) : nextValue }) }
  function remove(name: string) { const next = { ...values }; delete next[name]; onChange(next) }
  function add() { const name = key.trim(); if (!name || Object.hasOwn(values, name)) return; onChange({ ...values, [name]: value }); setKey(''); setValue('') }
  return <section><h2>{title}</h2><p className="page-description">Додаткові поля зберігаються разом із тестом.</p>{visible.map(([name, entry]) => <div className="metadata-row" key={name}><Field label={name}><Input value={textValue(entry)} onChange={e => update(name, e.target.value)} /></Field><Button type="button" variant="outline" onClick={() => remove(name)}>Прибрати</Button></div>)}<div className="metadata-row"><Field label="Назва поля"><Input value={key} onChange={e => setKey(e.target.value)} /></Field><Field label="Значення"><Input value={value} onChange={e => setValue(e.target.value)} /></Field><Button type="button" variant="outline" disabled={!key.trim() || Object.hasOwn(values, key.trim())} onClick={add}>Додати поле</Button></div></section>
}
