/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    // In production on Netlify, the /api/* redirect is handled by netlify.toml
    // This rewrite is only for local development
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
