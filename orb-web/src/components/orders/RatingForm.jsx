import { useState } from "react";
import { Star } from "lucide-react";
import Button from "../common/Button";

export default function RatingForm({ orderId, productId, status, rating: savedRating, review: savedReview, onSubmit }) {
  const [rating, setRating] = useState(0);
  const [review, setReview] = useState("");
  const [notice, setNotice] = useState("");
  if (savedRating) return <div className="submitted-rating"><div className="rating">{Array.from({ length: 5 }, (_, index) => <Star key={index} size={14} fill={index < savedRating ? "currentColor" : "none"}/>)}</div>{savedReview && <small>{savedReview}</small>}<small>Rating submitted</small></div>;
  if (status !== "Delivered") return <p className="rating-locked">Rating available after delivery.</p>;
  const submit = () => {
    if (!rating) { setNotice("Choose a star rating first."); return; }
    const result = onSubmit({ orderId, productId, rating, review });
    setNotice(result.message);
  };
  return <div className="rating-form"><span>Rate this product</span><div className="star-picker" role="radiogroup" aria-label="Product rating">{[1, 2, 3, 4, 5].map(value => <button type="button" key={value} aria-label={`${value} star${value > 1 ? "s" : ""}`} aria-checked={rating === value} role="radio" onClick={() => setRating(value)}><Star size={18} fill={value <= rating ? "currentColor" : "none"}/></button>)}</div><label className="review-field"><span>Review (optional)</span><textarea name="review" rows="2" maxLength="500" value={review} onChange={event => setReview(event.target.value)} placeholder="Share your experience"/></label><Button type="button" variant="outline" onClick={submit} disabled={!rating}>Submit Rating</Button>{notice && <small role="status">{notice}</small>}</div>;
}
