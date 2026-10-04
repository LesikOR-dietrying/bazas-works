// Adapted from shadcn/ui's MIT-licensed button component.
import * as React from 'react'
import { Slot } from '@radix-ui/react-slot'
import { cva } from 'class-variance-authority'
import type { VariantProps } from 'class-variance-authority'
import { cn } from '../../lib/utils'

const variants = cva('inline-flex items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2', {
  variants: { variant: {
    default: 'bg-baza-green text-white hover:bg-[#254f40]',
    outline: 'border border-[#d6dece] bg-white text-[#344c3d] hover:bg-[#eef3e8]',
    destructive: 'bg-red-700 text-white hover:bg-red-800',
  } }, defaultVariants: { variant: 'default' },
})

export function Button({ className, variant, asChild = false, type = 'button', ...props }:
  React.ComponentProps<'button'> & VariantProps<typeof variants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot : 'button'
  return <Comp type={asChild ? undefined : type} className={cn(variants({ variant, className }))} {...props} />
}
