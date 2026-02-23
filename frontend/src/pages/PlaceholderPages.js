import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { BookOpen, Construction } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Link } from 'react-router-dom';

const ComingSoon = ({ title, description, icon: Icon = Construction }) => {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card className="max-w-md w-full shadow-card text-center">
        <CardHeader className="space-y-4">
          <div className="mx-auto bg-primary/10 p-6 rounded-full w-fit">
            <Icon className="h-12 w-12 text-primary" />
          </div>
          <CardTitle className="text-3xl font-heading">{title}</CardTitle>
          <CardDescription className="text-base">{description}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-muted-foreground">
            This feature is currently under development and will be available soon.
          </p>
          <Link to="/dashboard">
            <Button className="w-full" data-testid="back-to-dashboard">
              Back to Dashboard
            </Button>
          </Link>
        </CardContent>
      </Card>
    </div>
  );
};

export const PYQPage = () => (
  <ComingSoon
    title="PYQ Section"
    description="Practice Previous Year Questions"
    icon={BookOpen}
  />
);

export const AssignedTestsPage = () => (
  <ComingSoon
    title="Assigned Tests"
    description="View Tests Assigned by Teacher"
    icon={BookOpen}
  />
);

export const ClassesPage = () => (
  <ComingSoon
    title="My Classes"
    description="Attend Live Classes"
    icon={BookOpen}
  />
);

export const AnalyticsPage = () => (
  <ComingSoon
    title="Analytics"
    description="Track Your Performance"
    icon={BookOpen}
  />
);

export const BookmarksPage = () => (
  <ComingSoon
    title="Bookmarks"
    description="Review Saved Questions"
    icon={BookOpen}
  />
);
