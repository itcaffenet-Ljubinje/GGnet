/**
 * Shared formatting utilities
 * Centralized formatting functions used across the application
 */

/**
 * Format bytes to human-readable string
 * @param bytes - Number of bytes
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted string (e.g., "1.5 GB")
 */
export function formatBytes(bytes: number, decimals: number = 2): string {
  if (bytes === 0) return '0 Bytes'
  if (bytes < 0) return 'Invalid'

  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB']

  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

/**
 * Format date to human-readable string
 * @param dateString - ISO date string or Date object
 * @param format - Format style: 'short', 'long', 'datetime', 'time' (default: 'short')
 * @returns Formatted date string
 */
export function formatDate(
  dateString: string | Date | null | undefined,
  format: 'short' | 'long' | 'datetime' | 'time' = 'short'
): string {
  if (!dateString) return 'N/A'

  const date = typeof dateString === 'string' ? new Date(dateString) : dateString

  if (isNaN(date.getTime())) return 'Invalid Date'

  const options: Intl.DateTimeFormatOptions = {
    short: { year: 'numeric', month: 'short', day: 'numeric' },
    long: { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' },
    datetime: { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' },
    time: { hour: '2-digit', minute: '2-digit', second: '2-digit' },
  }[format]

  return new Intl.DateTimeFormat('en-US', options).format(date)
}

/**
 * Format date and time together
 * @param dateString - ISO date string or Date object
 * @returns Formatted datetime string (e.g., "Jan 15, 2024, 3:45 PM")
 */
export function formatDateTime(dateString: string | Date | null | undefined): string {
  return formatDate(dateString, 'datetime')
}

/**
 * Format uptime in seconds to human-readable string
 * @param seconds - Uptime in seconds
 * @param fallback - Fallback string if invalid (default: 'N/A')
 * @returns Formatted uptime string (e.g., "2 days, 5 hours, 30 minutes")
 */
export function formatUptime(seconds: number | string | null | undefined, fallback: string = 'N/A'): string {
  if (seconds === null || seconds === undefined) return fallback

  const totalSeconds = typeof seconds === 'string' ? parseInt(seconds, 10) : seconds

  if (isNaN(totalSeconds) || totalSeconds < 0) return fallback

  const days = Math.floor(totalSeconds / 86400)
  const hours = Math.floor((totalSeconds % 86400) / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const secs = totalSeconds % 60

  const parts: string[] = []

  if (days > 0) parts.push(`${days} ${days === 1 ? 'day' : 'days'}`)
  if (hours > 0) parts.push(`${hours} ${hours === 1 ? 'hour' : 'hours'}`)
  if (minutes > 0 && days === 0) parts.push(`${minutes} ${minutes === 1 ? 'minute' : 'minutes'}`)
  if (secs > 0 && days === 0 && hours === 0) parts.push(`${secs} ${secs === 1 ? 'second' : 'seconds'}`)

  return parts.length > 0 ? parts.join(', ') : '0 seconds'
}

/**
 * Format duration in seconds to human-readable string
 * @param totalSeconds - Duration in seconds
 * @param showSeconds - Whether to show seconds for durations < 1 hour (default: false)
 * @returns Formatted duration string (e.g., "2h 30m" or "5m 30s")
 */
export function formatDuration(totalSeconds: number | null | undefined, showSeconds: boolean = false): string {
  if (totalSeconds === null || totalSeconds === undefined) return 'N/A'
  if (totalSeconds < 0) return 'Invalid'

  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = Math.floor(totalSeconds % 60)

  const parts: string[] = []

  if (hours > 0) {
    parts.push(`${hours}h`)
    parts.push(`${minutes}m`)
  } else if (minutes > 0) {
    parts.push(`${minutes}m`)
    if (showSeconds && seconds > 0) {
      parts.push(`${seconds}s`)
    }
  } else {
    parts.push(`${seconds}s`)
  }

  return parts.join(' ') || '0s'
}

/**
 * Format network speed
 * @param value - Speed value
 * @param unit - Unit: 'bps', 'Mbps', 'Gbps' (default: auto-detect)
 * @returns Formatted speed string (e.g., "100 Mbps")
 */
export function formatSpeed(value: number | null | undefined, unit?: 'bps' | 'Mbps' | 'Gbps'): string {
  if (value === null || value === undefined) return 'N/A'
  if (value < 0) return 'Invalid'

  if (unit) {
    return `${value.toFixed(2)} ${unit}`
  }

  // Auto-detect unit
  if (value >= 1000) {
    return `${(value / 1000).toFixed(2)} Gbps`
  } else {
    return `${value.toFixed(2)} Mbps`
  }
}

/**
 * Format percentage
 * @param value - Percentage value (0-100)
 * @param decimals - Number of decimal places (default: 1)
 * @returns Formatted percentage string (e.g., "45.5%")
 */
export function formatPercentage(value: number | null | undefined, decimals: number = 1): string {
  if (value === null || value === undefined) return 'N/A'
  if (isNaN(value)) return 'Invalid'

  return `${value.toFixed(decimals)}%`
}

/**
 * Format MAC address
 * @param mac - MAC address string
 * @returns Formatted MAC address (e.g., "00:11:22:33:44:55")
 */
export function formatMACAddress(mac: string | null | undefined): string {
  if (!mac) return 'N/A'

  // Remove any existing separators
  const cleaned = mac.replace(/[:-]/g, '').toUpperCase()

  // Must be 12 hex characters
  if (!/^[0-9A-F]{12}$/.test(cleaned)) return mac

  // Format as XX:XX:XX:XX:XX:XX
  return cleaned.match(/.{2}/g)?.join(':') || mac
}

/**
 * Format IP address
 * @param ip - IP address string
 * @returns Formatted IP address (validates IPv4)
 */
export function formatIPAddress(ip: string | null | undefined): string {
  if (!ip) return 'N/A'

  // Basic IPv4 validation
  const ipv4Regex = /^(\d{1,3}\.){3}\d{1,3}$/
  if (ipv4Regex.test(ip)) {
    return ip
  }

  // Return as-is if it might be IPv6 or hostname
  return ip
}

/**
 * Format number with thousand separators
 * @param value - Number to format
 * @param decimals - Number of decimal places (default: 0)
 * @returns Formatted number (e.g., "1,234,567")
 */
export function formatNumber(value: number | null | undefined, decimals: number = 0): string {
  if (value === null || value === undefined) return 'N/A'
  if (isNaN(value)) return 'Invalid'

  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}




