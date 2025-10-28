import './style.css';   // ✅ Import your global stylesheet here

export default function MyApp({ Component, pageProps }) {
  // Next.js renders *every* page through this component
  return <Component {...pageProps} />;
}