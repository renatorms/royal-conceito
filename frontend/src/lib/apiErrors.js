/**
 * Maps a DRF error payload onto a react-hook-form instance.
 *
 * DRF errors come in two shapes:
 *   - field-specific: { campo: ["mensagem"] }
 *   - general:        { detail: "mensagem" }
 *
 * Field errors are attached via setError so they render next to the input;
 * general errors are handed to setGeneralError for a banner above the form.
 */
export function applyApiErrors(errorData, setError, setGeneralError) {
  if (!errorData || typeof errorData !== "object") {
    setGeneralError("Ocorreu um erro inesperado. Tente novamente.");
    return;
  }

  if (errorData.detail) {
    setGeneralError(errorData.detail);
    return;
  }

  let hasFieldError = false;
  for (const [field, messages] of Object.entries(errorData)) {
    if (Array.isArray(messages) && messages.length > 0) {
      setError(field, { type: "server", message: messages[0] });
      hasFieldError = true;
    }
  }

  if (!hasFieldError) {
    setGeneralError("Ocorreu um erro inesperado. Tente novamente.");
  }
}
