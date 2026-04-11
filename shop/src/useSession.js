import { useState, useEffect } from 'react'

export function useSession() {
  const [sessionId] = useState(() => {
    let id = localStorage.getItem('cart_session_id')
    if (!id) {
      id = crypto.randomUUID()
      localStorage.setItem('cart_session_id', id)
    }
    return id
  })
  return sessionId
}
