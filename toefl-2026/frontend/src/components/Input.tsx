import React from 'react';
import styles from './Input.module.css';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string;
    helperText?: string;
    fullWidth?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
    ({ className, label, error, helperText, fullWidth = true, ...props }, ref) => {
        const containerClasses = [
            styles.container,
            fullWidth ? styles.fullWidth : '',
            error ? styles.hasError : '',
        ].filter(Boolean).join(' ');

        const inputClasses = [
            styles.input,
            error ? styles.inputError : '',
            className,
        ].filter(Boolean).join(' ');

        return (
            <div className={containerClasses}>
                {label && (
                    <label className={styles.label} htmlFor={props.id}>
                        {label}
                    </label>
                )}
                <input
                    ref={ref}
                    className={inputClasses}
                    aria-invalid={!!error}
                    aria-describedby={error ? `${props.id}-error` : helperText ? `${props.id}-helper` : undefined}
                    {...props}
                />
                {error && (
                    <span id={`${props.id}-error`} className={styles.errorText}>
                        {error}
                    </span>
                )}
                {helperText && !error && (
                    <span id={`${props.id}-helper`} className={styles.helperText}>
                        {helperText}
                    </span>
                )}
            </div>
        );
    }
);
Input.displayName = 'Input';
