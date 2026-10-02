export function apiErrorMessage(error, { notFound = "The requested item was not found." } = {}) {
  if (error?.status === 401) return "Your session has expired. Please sign in again.";
  if (error?.status === 403) {
    return error.message || "You do not have permission to perform this action.";
  }
  if (error?.status === 404) return error.message || notFound;
  if (error?.status === 409 || error?.status === 422) return error.message || "Please review the submitted values.";
  if (!error?.status) return "Could not reach the ORB service. Check your connection and try again.";
  return error.message || "The request could not be completed. Please try again.";
}
