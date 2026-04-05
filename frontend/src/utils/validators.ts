/**
 * Shared validation utilities
 * Centralized validation functions used across the application
 */

/**
 * Validate MAC address format
 * @param mac - MAC address string
 * @returns true if valid MAC address
 */
export function validateMACAddress(mac: string): boolean {
  if (!mac) return false

  // Remove separators for validation
  const cleaned = mac.replace(/[:-]/g, '').toUpperCase()

  // Must be exactly 12 hex characters
  return /^[0-9A-F]{12}$/.test(cleaned)
}

/**
 * Validate IP address (IPv4)
 * @param ip - IP address string
 * @returns true if valid IPv4 address
 */
export function validateIPAddress(ip: string): boolean {
  if (!ip) return false

  const parts = ip.split('.')
  if (parts.length !== 4) return false

  return parts.every(part => {
    const num = parseInt(part, 10)
    return !isNaN(num) && num >= 0 && num <= 255
  })
}

/**
 * Validate email address
 * @param email - Email address string
 * @returns true if valid email format
 */
export function validateEmail(email: string): boolean {
  if (!email) return false

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * Validate required field
 * @param value - Value to check
 * @returns true if value is not empty
 */
export function validateRequired(value: string | number | null | undefined): boolean {
  if (value === null || value === undefined) return false
  if (typeof value === 'string') return value.trim().length > 0
  if (typeof value === 'number') return !isNaN(value)
  return true
}

/**
 * Validate port number
 * @param port - Port number
 * @returns true if valid port (1-65535)
 */
export function validatePort(port: number | string): boolean {
  const num = typeof port === 'string' ? parseInt(port, 10) : port
  return !isNaN(num) && num >= 1 && num <= 65535
}

/**
 * Validate hostname
 * @param hostname - Hostname string
 * @returns true if valid hostname format
 */
export function validateHostname(hostname: string): boolean {
  if (!hostname) return false

  // Basic hostname validation: alphanumeric, dots, hyphens, underscores
  // Must start and end with alphanumeric
  const hostnameRegex = /^[a-zA-Z0-9]([a-zA-Z0-9-_.]{0,61}[a-zA-Z0-9])?$/
  return hostnameRegex.test(hostname)
}

/**
 * Validate URL
 * @param url - URL string
 * @returns true if valid URL format
 */
export function validateURL(url: string): boolean {
  if (!url) return false

  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

/**
 * Validate positive number
 * @param value - Number to validate
 * @returns true if positive number
 */
export function validatePositiveNumber(value: number | string): boolean {
  const num = typeof value === 'string' ? parseFloat(value) : value
  return !isNaN(num) && num > 0
}

/**
 * Validate non-negative number
 * @param value - Number to validate
 * @returns true if non-negative number
 */
export function validateNonNegativeNumber(value: number | string): boolean {
  const num = typeof value === 'string' ? parseFloat(value) : value
  return !isNaN(num) && num >= 0
}

/**
 * Validate number range
 * @param value - Number to validate
 * @param min - Minimum value (inclusive)
 * @param max - Maximum value (inclusive)
 * @returns true if number is within range
 */
export function validateNumberRange(value: number | string, min: number, max: number): boolean {
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) return false
  return num >= min && num <= max
}

/**
 * Validate percentage (0-100)
 * @param value - Percentage value
 * @returns true if valid percentage
 */
export function validatePercentage(value: number | string): boolean {
  return validateNumberRange(value, 0, 100)
}




