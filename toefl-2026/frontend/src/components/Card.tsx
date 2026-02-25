import React from 'react';
import styles from './Card.module.css';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
    children: React.ReactNode;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
    ({ className, children, ...props }, ref) => (
        <div ref={ref} className={`${styles.card} ${className || ''}`} {...props}>
            {children}
        </div>
    )
);
Card.displayName = 'Card';

export const CardHeader = ({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
    <div className={`${styles.cardHeader} ${className || ''}`} {...props}>{children}</div>
);
CardHeader.displayName = 'CardHeader';

export const CardTitle = ({ className, children, ...props }: React.HTMLAttributes<HTMLHeadingElement>) => (
    <h3 className={`${styles.cardTitle} ${className || ''}`} {...props}>{children}</h3>
);
CardTitle.displayName = 'CardTitle';

export const CardContent = ({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
    <div className={`${styles.cardContent} ${className || ''}`} {...props}>{children}</div>
);
CardContent.displayName = 'CardContent';

export const CardFooter = ({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
    <div className={`${styles.cardFooter} ${className || ''}`} {...props}>{children}</div>
);
CardFooter.displayName = 'CardFooter';
