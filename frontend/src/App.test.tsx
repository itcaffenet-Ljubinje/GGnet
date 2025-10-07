// ULTRA MINIMAL APP - Just to test if React renders AT ALL

export default function AppTest() {
  console.log('=== APP TEST RENDERING ===')
  
  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(to bottom right, #1a1a2e, #16213e, #0f3460)',
      color: 'white',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '40px',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <div style={{ textAlign: 'center', maxWidth: '600px' }}>
        <h1 style={{ 
          fontSize: '64px', 
          marginBottom: '20px',
          background: 'linear-gradient(45deg, #00d4ff, #0066ff)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text'
        }}>
          🚀 GGnet
        </h1>
        
        <h2 style={{ 
          fontSize: '32px', 
          marginBottom: '30px',
          color: '#00d4ff'
        }}>
          React is Working!
        </h2>
        
        <div style={{ 
          background: 'rgba(255,255,255,0.1)', 
          padding: '30px', 
          borderRadius: '12px',
          marginBottom: '20px'
        }}>
          <p style={{ fontSize: '18px', marginBottom: '15px', lineHeight: '1.6' }}>
            ✅ <strong>Backend:</strong> Running on port 8000<br/>
            ✅ <strong>Frontend:</strong> Running on port 3000<br/>
            ✅ <strong>React:</strong> Rendering successfully<br/>
            ✅ <strong>Login:</strong> admin / admin123
          </p>
        </div>
        
        <div style={{ 
          background: 'rgba(0, 212, 255, 0.1)', 
          border: '2px solid #00d4ff',
          padding: '20px', 
          borderRadius: '8px',
          fontSize: '14px',
          textAlign: 'left'
        }}>
          <p style={{ marginBottom: '10px' }}>
            <strong>Next Steps:</strong>
          </p>
          <ol style={{ marginLeft: '20px', lineHeight: '1.8' }}>
            <li>Open Developer Console (F12)</li>
            <li>Check for any errors in Console tab</li>
            <li>If you see this, React works!</li>
            <li>The problem was with CSS/Tailwind or complex components</li>
          </ol>
        </div>
        
        <p style={{ 
          marginTop: '30px', 
          fontSize: '12px', 
          color: '#666',
          fontStyle: 'italic'
        }}>
          This is a temporary test page. Original login will be restored once we fix the issue.
        </p>
      </div>
    </div>
  )
}
