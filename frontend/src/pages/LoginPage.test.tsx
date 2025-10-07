// MINIMAL TEST VERSION - Just to see if ANYTHING renders
export default function LoginPageTest() {
  console.log('=== MINIMAL LOGIN PAGE RENDERING ===')
  
  return (
    <div style={{ 
      minHeight: '100vh', 
      background: '#1a1a1a', 
      color: 'white',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: '24px',
      padding: '20px',
      textAlign: 'center'
    }}>
      <div>
        <h1 style={{ marginBottom: '20px', fontSize: '48px' }}>
          ✅ REACT WORKS!
        </h1>
        <p style={{ marginBottom: '20px' }}>
          If you see this, React is rendering properly.
        </p>
        <p style={{ fontSize: '16px', color: '#888' }}>
          The problem was with CSS or component complexity.
        </p>
      </div>
    </div>
  )
}

