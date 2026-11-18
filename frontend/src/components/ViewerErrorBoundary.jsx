import { Component } from "react";

// Catches model-loading errors (404, corrupt .glb, CORS) so the app doesn't go blank.
export default class ViewerErrorBoundary extends Component {
  state = { error: null };

  static getDerivedStateFromError(error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <div className="stage-message">
          <p className="error">This model could not be loaded.</p>
          <p className="muted">
            The file may be missing, corrupt, or blocked by the server. Check the browser console for details.
          </p>
        </div>
      );
    }
    return this.props.children;
  }
}
