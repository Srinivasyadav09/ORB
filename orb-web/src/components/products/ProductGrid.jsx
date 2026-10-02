import ProductCard from "./ProductCard";

export default function ProductGrid({ products, onAdd }) {
  return <div className="product-grid">{products.map(product => <ProductCard key={product.id} product={product} onAdd={onAdd}/>)}</div>;
}
