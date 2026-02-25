import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { BookOpen, Construction, Clock, FileText, BarChart3, Bookmark } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Link } from 'react-router-dom';

const ComingSoon = ({ title, description, icon: Icon = Construction, message }) => {
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
            {message || "This feature is currently under development and will be available soon."}
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
    description="Tests Assigned by Your Teacher"
    icon={FileText}
    message="No tests uploaded yet for you. Your teacher will assign tests soon."
  />
);

export const ClassesPage = () => (
  <ComingSoon
    title="My Classes"
    description="Live and Recorded Classes"
    icon={BookOpen}
    message="No classes yet. Check back later for upcoming live classes."
  />
);

export const AnalyticsPage = () => (
  <ComingSoon
    title="Analytics"
    description="Track Your Performance"
    icon={BarChart3}
    message="This feature is coming soon! You'll be able to track your detailed performance analytics here."
  />
);

export const BookmarksPage = () => (
  <ComingSoon
    title="Bookmarks"
    description="Review Saved Questions"
    icon={Bookmark}
    message="This feature is coming soon! You'll be able to save and review important questions here."
  />
);

export const MyTestsPage = () => (
  <ComingSoon
    title="My Tests"
    description="Create Custom Practice Tests"
    icon={Clock}
    message="This feature will be available soon! You'll be able to create personalized practice tests."
  />
);
