/** @type {import('tailwindcss').Config} */
// tailwind.config.js
module.exports = {
  content: [
    './templates/**/*.html',
    './static/css/styles.css',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#1D4ED8',  // Deep blue for buttons and accents
        secondary: '#60A5FA', // Light blue for hover effects
        accent: '#FBBF24',    // Bright yellow for highlights
        background: '#F3F4F6', // Light gray background
        cardBackground: '#FFFFFF', // White for cards
        cardBorder: '#E5E7EB', // Light gray for borders
        textPrimary: '#111827', // Dark gray for text
        textSecondary: '#6B7280', // Gray for subtext
        connected: '#10B981', // Green for connected status
        disconnected: '#EF4444', // Red for disconnected status
      },
      fontSize: {
        'status': '0.875rem', // Custom font size for status text (14px)
      },
      fontWeight: {
        'status': '600', // Semi-bold weight for status text
      },
      spacing: {
        'status-padding': '0.25rem 0.5rem', // Padding for status text
      }
    },
  },
  plugins: [],
}
