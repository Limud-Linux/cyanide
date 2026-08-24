class ProgressObserver:
    """Interface for receiving installation progress updates."""
    
    def on_progress(self, percent: int, stage: str, message: str):
        """Called when progress is made.
        
        Args:
            percent: 0-100 completion estimate
            stage: Short string describing the current phase (e.g. 'partitioning')
            message: Detailed log message
        """
        pass

    def on_finished(self, success: bool, details: str):
        """Called when the installation finishes or fails.
        
        Args:
            success: True if completed successfully, False otherwise
            details: Error message if failed, or success summary
        """
        pass
