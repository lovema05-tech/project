import { useState, useEffect } from 'react'
import { supabase } from './supabase'
import { useSession } from './useSession'
import './App.css'

function ProductCard({ product, onAddToCart }) {
  return (
    <div className="product-card">
      <img src={product.image_url} alt={product.name} />
      <div className="product-info">
        <span className="product-category">{product.category}</span>
        <h3>{product.name}</h3>
        <p>{product.description}</p>
        <div className="product-footer">
          <span className="price">₩{product.price.toLocaleString()}</span>
          <button
            className="add-btn"
            onClick={() => onAddToCart(product)}
            disabled={product.stock === 0}
          >
            {product.stock === 0 ? '품절' : '담기'}
          </button>
        </div>
      </div>
    </div>
  )
}

function CartSidebar({ cartItems, products, onUpdateQty, onRemove, onClose, onCheckout }) {
  const total = cartItems.reduce((sum, item) => {
    const product = products.find(p => p.id === item.product_id)
    return sum + (product ? product.price * item.quantity : 0)
  }, 0)

  return (
    <div className="cart-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="cart-sidebar">
        <div className="cart-header">
          <h2>장바구니</h2>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        {cartItems.length === 0 ? (
          <div className="cart-empty">
            <span>🛒</span>
            <p>장바구니가 비어있습니다.</p>
          </div>
        ) : (
          <>
            <div className="cart-items">
              {cartItems.map(item => {
                const product = products.find(p => p.id === item.product_id)
                if (!product) return null
                return (
                  <div key={item.id} className="cart-item">
                    <img src={product.image_url} alt={product.name} />
                    <div className="cart-item-info">
                      <span className="cart-item-name">{product.name}</span>
                      <span className="cart-item-price">₩{(product.price * item.quantity).toLocaleString()}</span>
                      <div className="qty-control">
                        <button onClick={() => onUpdateQty(item, item.quantity - 1)}>−</button>
                        <span>{item.quantity}</span>
                        <button onClick={() => onUpdateQty(item, item.quantity + 1)}>+</button>
                      </div>
                    </div>
                    <button className="remove-btn" onClick={() => onRemove(item)}>🗑</button>
                  </div>
                )
              })}
            </div>
            <div className="cart-footer">
              <div className="cart-total">
                <span>합계</span>
                <span className="total-price">₩{total.toLocaleString()}</span>
              </div>
              <button className="checkout-btn" onClick={onCheckout}>결제하기</button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default function App() {
  const sessionId = useSession()
  const [products, setProducts] = useState([])
  const [cartItems, setCartItems] = useState([])
  const [cartOpen, setCartOpen] = useState(false)
  const [category, setCategory] = useState('전체')
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState(null)

  const categories = ['전체', ...new Set(products.map(p => p.category))]
  const cartCount = cartItems.reduce((s, i) => s + i.quantity, 0)

  useEffect(() => {
    fetchProducts()
    fetchCart()
  }, [])

  async function fetchProducts() {
    const { data } = await supabase.from('products').select('*').order('created_at')
    if (data) setProducts(data)
    setLoading(false)
  }

  async function fetchCart() {
    const { data } = await supabase
      .from('cart_items')
      .select('*')
      .eq('session_id', sessionId)
    if (data) setCartItems(data)
  }

  function showToast(msg) {
    setToast(msg)
    setTimeout(() => setToast(null), 2200)
  }

  async function addToCart(product) {
    const existing = cartItems.find(i => i.product_id === product.id)
    if (existing) {
      await updateQty(existing, existing.quantity + 1)
    } else {
      const { data, error } = await supabase
        .from('cart_items')
        .insert({ session_id: sessionId, product_id: product.id, quantity: 1 })
        .select()
        .single()
      if (!error && data) {
        setCartItems(prev => [...prev, data])
      }
    }
    showToast(`${product.name}이(가) 담겼습니다!`)
  }

  async function updateQty(item, newQty) {
    if (newQty <= 0) {
      await removeItem(item)
      return
    }
    const { data, error } = await supabase
      .from('cart_items')
      .update({ quantity: newQty })
      .eq('id', item.id)
      .select()
      .single()
    if (!error && data) {
      setCartItems(prev => prev.map(i => i.id === item.id ? data : i))
    }
  }

  async function removeItem(item) {
    await supabase.from('cart_items').delete().eq('id', item.id)
    setCartItems(prev => prev.filter(i => i.id !== item.id))
  }

  async function checkout() {
    await supabase.from('cart_items').delete().eq('session_id', sessionId)
    setCartItems([])
    setCartOpen(false)
    showToast('주문이 완료되었습니다! 감사합니다 🎉')
  }

  const filtered = category === '전체' ? products : products.filter(p => p.category === category)

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <h1 className="logo">🛍 ShopMart</h1>
          <button className="cart-btn" onClick={() => setCartOpen(true)}>
            🛒 장바구니
            {cartCount > 0 && <span className="cart-badge">{cartCount}</span>}
          </button>
        </div>
      </header>

      <main className="main">
        <div className="category-bar">
          {categories.map(c => (
            <button
              key={c}
              className={`cat-btn ${category === c ? 'active' : ''}`}
              onClick={() => setCategory(c)}
            >
              {c}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="loading">상품을 불러오는 중...</div>
        ) : (
          <div className="product-grid">
            {filtered.map(product => (
              <ProductCard key={product.id} product={product} onAddToCart={addToCart} />
            ))}
          </div>
        )}
      </main>

      {cartOpen && (
        <CartSidebar
          cartItems={cartItems}
          products={products}
          onUpdateQty={updateQty}
          onRemove={removeItem}
          onClose={() => setCartOpen(false)}
          onCheckout={checkout}
        />
      )}

      {toast && <div className="toast">{toast}</div>}
    </div>
  )
}
