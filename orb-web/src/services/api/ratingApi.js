import { ApiError } from "./client";

// The current FastAPI application has no ratings routes. Keep callers explicit
// about that until a backend contract is added; do not send requests to /ratings.
const unavailable = () => {
  throw new ApiError("Ratings are not currently supported by the ORB API.");
};

export const ratingApi = Object.freeze({
  available: false,
  list: unavailable,
  create: unavailable
});
