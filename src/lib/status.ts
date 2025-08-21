// Status management for backend connectivity

export interface BackendStatus {
  isConnected: boolean;
  lastCheck: Date | null;
  error: string | null;
  channels: string[];
}

class BackendStatusManager {
  private status: BackendStatus = {
    isConnected: false,
    lastCheck: null,
    error: null,
    channels: [],
  };

  private listeners: Set<(status: BackendStatus) => void> = new Set();

  getStatus(): BackendStatus {
    return { ...this.status };
  }

  updateStatus(updates: Partial<BackendStatus>) {
    this.status = { ...this.status, ...updates };
    this.notifyListeners();
  }

  subscribe(listener: (status: BackendStatus) => void) {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  }

  private notifyListeners() {
    this.listeners.forEach(listener => listener(this.status));
  }
}

export const backendStatusManager = new BackendStatusManager();
