import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    console.error('ErrorBoundary caught an error:', error, info);
  }

  handleReload = () => {
    this.setState({ hasError: false });
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="mt-6 text-center p-8">
          <h2 className="text-xl font-bold text-red-700 mb-2">Something went wrong</h2>
          <p className="text-gray-600 mb-4">This page failed to load. Please go back and try again.</p>
          <button onClick={this.handleReload} className="text-blue-600 underline">Back to Home</button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;