// Performance optimizations

// Throttle function
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Debounce function
function debounce(func, delay) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

// Batch DOM updates
class DOMBatcher {
    constructor() {
        this.updates = [];
        this.scheduled = false;
    }

    add(updateFn) {
        this.updates.push(updateFn);
        if (!this.scheduled) {
            this.scheduled = true;
            requestAnimationFrame(() => this.flush());
        }
    }

    flush() {
        const updates = this.updates.splice(0);
        updates.forEach(fn => fn());
        this.scheduled = false;
    }
}

// Export for use in main app.js
window.perfUtils = { 
    throttle, 
    debounce,
    domBatcher: new DOMBatcher()
};

