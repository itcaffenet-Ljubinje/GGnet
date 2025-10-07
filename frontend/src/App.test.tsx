// ULTRA MINIMAL APP - Just to test if React renders AT ALL

function AppTest() {
  console.log('=== APP TEST RENDERING ===')
  
  const containerStyle = {
    minHeight: '100vh',
    background: '#1a1a2e',
    color: 'white',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '40px',
    fontFamily: 'Arial, sans-serif'
  }
  
  const headingStyle = {
    fontSize: '64px',
    marginBottom: '20px',
    color: '#00d4ff'
  }
  
  const textStyle = {
    fontSize: '24px',
    marginBottom: '20px'
  }
  
  return (
    <div style={containerStyle}>
      <div style={{ textAlign: 'center' }}>
        <h1 style={headingStyle}>
          REACT WORKS!
        </h1>
        <p style={textStyle}>
          If you see this text, React is rendering.
        </p>
        <p style={{ fontSize: '16px', color: '#888' }}>
          Backend: http://localhost:8000
        </p>
        <p style={{ fontSize: '16px', color: '#888' }}>
          Login: admin / admin123
        </p>
      </div>
    </div>
  )
}

export default AppTest
