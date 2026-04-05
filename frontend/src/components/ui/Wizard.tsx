/**
 * Wizard Component
 * Multi-step wizard for complex forms
 */

import { ReactNode, useState } from 'react'
import { clsx } from 'clsx'
import { Button } from './Button'
import { ChevronLeft, ChevronRight, Check } from 'lucide-react'

export interface WizardStep {
  id: string
  title: string
  description?: string
  content: ReactNode
  isValid?: () => boolean
}

interface WizardProps {
  steps: WizardStep[]
  onComplete: (data: Record<string, unknown>) => void
  onCancel?: () => void
  initialStep?: number
  className?: string
}

export function Wizard({ 
  steps, 
  onComplete, 
  onCancel,
  initialStep = 0,
  className 
}: WizardProps) {
  const [currentStep, setCurrentStep] = useState(initialStep)
  const [formData, setFormData] = useState<Record<string, unknown>>({})

  const currentStepData = steps[currentStep]
  const isFirstStep = currentStep === 0
  const isLastStep = currentStep === steps.length - 1
  const canProceed = currentStepData.isValid ? currentStepData.isValid() : true

  const handleNext = () => {
    if (isLastStep) {
      onComplete(formData)
    } else {
      setCurrentStep(currentStep + 1)
    }
  }

  const handlePrevious = () => {
    if (!isFirstStep) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleCancel = () => {
    if (onCancel) {
      onCancel()
    }
  }

  return (
    <div className={clsx('wizard', className)}>
      {/* Progress Indicator */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          {steps.map((step, index) => (
            <div key={step.id} className="flex items-center flex-1">
              <div className="flex flex-col items-center flex-1">
                <div
                  className={clsx(
                    'w-10 h-10 rounded-full flex items-center justify-center border-2 transition-colors',
                    index < currentStep
                      ? 'bg-green-500 border-green-500 text-white'
                      : index === currentStep
                      ? 'bg-blue-500 border-blue-500 text-white'
                      : 'bg-white border-gray-300 text-gray-400'
                  )}
                >
                  {index < currentStep ? (
                    <Check className="w-5 h-5" />
                  ) : (
                    <span>{index + 1}</span>
                  )}
                </div>
                <div className="mt-2 text-center">
                  <p
                    className={clsx(
                      'text-xs font-medium',
                      index <= currentStep ? 'text-gray-900' : 'text-gray-400'
                    )}
                  >
                    {step.title}
                  </p>
                </div>
              </div>
              {index < steps.length - 1 && (
                <div
                  className={clsx(
                    'flex-1 h-0.5 mx-2',
                    index < currentStep ? 'bg-green-500' : 'bg-gray-300'
                  )}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div className="mb-6">
        {currentStepData.description && (
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            {currentStepData.description}
          </p>
        )}
        <div className="min-h-[300px]">
          {currentStepData.content}
        </div>
      </div>

      {/* Navigation Buttons */}
      <div className="flex justify-between items-center pt-4 border-t border-gray-200 dark:border-gray-700">
        <div>
          {onCancel && (
            <Button
              onClick={handleCancel}
              variant="outline"
              size="md"
            >
              Cancel
            </Button>
          )}
        </div>
        <div className="flex gap-2">
          {!isFirstStep && (
            <Button
              onClick={handlePrevious}
              variant="outline"
              size="md"
              leftIcon={<ChevronLeft className="w-4 h-4" />}
            >
              Previous
            </Button>
          )}
          <Button
            onClick={handleNext}
            variant="primary"
            size="md"
            disabled={!canProceed}
            rightIcon={isLastStep ? <Check className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          >
            {isLastStep ? 'Complete' : 'Next'}
          </Button>
        </div>
      </div>
    </div>
  )
}




